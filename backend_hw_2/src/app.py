from fastapi import FastAPI, status, HTTPException
from transformers import AutoModel, AutoTokenizer
import torch
from contextlib import asynccontextmanager

models = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    model_name = "sergeyzh/rubert-mini-frida"
    models["tokenizer"] = AutoTokenizer.from_pretrained(model_name)
    models["model"] = AutoModel.from_pretrained(model_name)
    models["model"].eval()
    yield
    models.clear()


app = FastAPI(lifespan=lifespan)


@app.get("/", status_code=status.HTTP_200_OK)
def root():
    return {"message": "Hello from Embedder Service!", "instruction": "Send a POST request to /embed to get embeddings using sergeyzh/rubert-mini"}


@app.get("/health", status_code=status.HTTP_200_OK)
def health():
    if not models:
        raise HTTPException(status_code=503, detail="Model not loaded")

    return {"status": "OK"}


@app.post("/embed")
def embed(input: str):
    try:
        tokenizer = models["tokenizer"]
        model = models["model"]

        tokenized_input = tokenizer(input, max_length=512, padding=True, truncation=True, return_tensors="pt")

        with torch.no_grad():
            outputs = model(**tokenized_input)

        embedding = outputs.last_hidden_state[:, 0, :].flatten().tolist()

        return {"embedding": embedding, "status": "success"}

    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
