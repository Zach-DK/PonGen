# Generative Physics: Pong

A real-time neural network that learns to predict the next frame of Pong gameplay, creating a generative physics simulation trained on actual game data.

![Example Generation](https://github.com/user-attachments/assets/005f9443-fb35-43e5-9ded-4f0b08a1d0a2)

## Overview

This project attempts to implements a lightweight U-Net model that learns Pong physics by predicting the next frame given the previous two frames. The model captures ball movement, paddle physics, collisions, and game dynamics entirely from visual data.

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies (CUDA edition recommended for GPU acceleration, check version)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
pip install numpy pillow matplotlib imageio[ffmpeg] pygame
```

### 2. Record Training Data

```bash
python pong.py
```

- Play the game using arrow keys
- Press **F1** to start/stop recording frames
- Record several gameplay sessions for diverse training data

### 3. Train the Model

Open `pongmodel.ipynb` and run the cells:

1. **Data Loading**: Loads recorded frames into sequences
2. **Model Creation**: Builds the U-Net architecture
3. **Training**: Trains for 40 epochs with weighted loss
4. **Generation**: Creates autonomous gameplay videos

### 4. Generate Autonomous Gameplay

```python
# Generate 1800 frames (30 seconds at 60fps)
out_dir = generate_gameplay(num_frames=1800, fps=60, model_path="pong_model_final.pth")
```

## Architecture

### Model: RealTimePongPredictor

- **Input**: Two consecutive frames [batch, 2, 200, 200]
- **Output**: Predicted next frame [batch, 1, 200, 200]
- **Control Processing**: Extracts player input from bottom row pixels
- **Skip Connections**: U-Net architecture with encoder-decoder structure
- **Residual Prediction**: Predicts frame delta rather than absolute values

### Training Strategy

- **Weighted Loss**: Emphasizes white pixels (ball, paddles) over background
- **Sequence Learning**: Uses consecutive frame triplets (t-1, t) → t+1
- **Control Conditioning**: Learns to respond to player input encoding
- **Real-time Optimization**: Batch normalization and efficient convolutions

## File Structure

```
Pong/
├── pong.py                 # Original Pong game with frame recording
├── pongmodel.ipynb         # Main training and generation notebook
├── transformer.ipynb       # Alternative Transformer implementation
├── frames/                 # Recorded training frames (created by F1)
├── generated_*/            # Generated gameplay videos
├── pong_model_final.pth    # Trained model weights
└── README.md              # This file
```
