"""
Visual understanding: what is on screen, not just what is said.

keyframes - pick the frames worth looking at (scene changes, with a
            floor and a ceiling on how often), via ffmpeg.
describer - ask a vision-language model (Ollama, e.g. qwen2.5vl) for
            each frame's on-screen text and a one-line description.
segments  - merge consecutive frames showing the same thing, turn
            them into text that search/RAG can use, and say how
            related each one is to what was being said at the time.
"""
