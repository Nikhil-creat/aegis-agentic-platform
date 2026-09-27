"""
Per-language sandbox image and invocation configuration.
Designed and Developed by NIKHIL CHARY SRIRAMOJU
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class LanguageConfig:
    image: str
    filename: str
    compile_cmd: list[str] | None
    run_cmd: list[str]


LANGUAGE_CONFIGS: dict[str, LanguageConfig] = {
    "python": LanguageConfig(
        image="python:3.11-slim",
        filename="main.py",
        compile_cmd=None,
        run_cmd=["python", "main.py"],
    ),
    "javascript": LanguageConfig(
        image="node:20-slim",
        filename="main.js",
        compile_cmd=None,
        run_cmd=["node", "main.js"],
    ),
    "java": LanguageConfig(
        image="eclipse-temurin:21-jdk-alpine",
        filename="Main.java",
        compile_cmd=["javac", "Main.java"],
        run_cmd=["java", "Main"],
    ),
    "c": LanguageConfig(
        image="gcc:13-bookworm",
        filename="main.c",
        compile_cmd=["gcc", "main.c", "-o", "main"],
        run_cmd=["./main"],
    ),
    "shell": LanguageConfig(
        image="bash:5",
        filename="script.sh",
        compile_cmd=None,
        run_cmd=["bash", "script.sh"],
    ),
    "html": LanguageConfig(
        image="node:20-slim",
        filename="index.html",
        compile_cmd=None,
        run_cmd=["cat", "index.html"],  # rendered client-side; sandbox validates syntax only
    ),
    "reactjs": LanguageConfig(
        image="node:20-slim",
        filename="App.jsx",
        compile_cmd=["npx", "--yes", "esbuild", "App.jsx", "--bundle", "--outfile=bundle.js"],
        run_cmd=["node", "bundle.js"],
    ),
}
