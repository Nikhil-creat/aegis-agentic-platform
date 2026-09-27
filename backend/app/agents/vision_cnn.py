"""
CNN Vision Sub-system.

A lightweight PyTorch CNN (transfer-learning ready) that extracts structured
feature embeddings from screenshots / UI wireframes / architecture diagrams,
so the agent graph and RAG pipeline can reason over visual context.

Exposed standalone as `vision-service` (see Dockerfile.vision) but importable
directly for in-process use during development.

Designed and Developed by NIKHIL CHARY SRIRAMOJU
"""
from __future__ import annotations

import io

import torch
import torch.nn as nn
import torch.nn.functional as F
from fastapi import FastAPI, File, UploadFile
from PIL import Image
from torchvision import transforms
from torchvision.models import resnet18, ResNet18_Weights

app = FastAPI(title="Aegis Vision CNN Service")

_PREPROCESS = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


class DiagramClassifierHead(nn.Module):
    """A small classification/embedding head stacked on a frozen ResNet18
    backbone — classifies visual input into {ui_wireframe, architecture_diagram,
    screenshot, chart, other} and emits a 128-d embedding for RAG fusion."""

    NUM_CLASSES = 5

    def __init__(self) -> None:
        super().__init__()
        backbone = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)
        backbone.fc = nn.Identity()
        for param in backbone.parameters():
            param.requires_grad = False  # frozen feature extractor
        self.backbone = backbone
        self.embed = nn.Linear(512, 128)
        self.classifier = nn.Linear(128, self.NUM_CLASSES)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        features = self.backbone(x)
        embedding = F.relu(self.embed(features))
        logits = self.classifier(embedding)
        return embedding, logits


_model = DiagramClassifierHead()
_model.eval()

_CLASS_NAMES = ["ui_wireframe", "architecture_diagram", "screenshot", "chart", "other"]


def extract_visual_features(image_bytes: bytes) -> dict:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    tensor = _PREPROCESS(image).unsqueeze(0)
    with torch.no_grad():
        embedding, logits = _model(tensor)
        probs = F.softmax(logits, dim=-1).squeeze().tolist()
    predicted_class = _CLASS_NAMES[int(torch.argmax(logits))]
    return {
        "predicted_class": predicted_class,
        "class_probabilities": dict(zip(_CLASS_NAMES, probs)),
        "embedding": embedding.squeeze().tolist(),
    }


@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...)) -> dict:
    content = await file.read()
    result = extract_visual_features(content)
    return {"filename": file.filename, **result}


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "vision-cnn"}
