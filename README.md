# ALINet

The goal of this project is to utilise video lectures to generate high-quality
questions pertinent to the provided educational content.

It accompanies the paper "Examining the Feasibility of AI-Generated Questions in Educational Settings" submitted to [TAS 2024](https://symposium.tas.ac.uk/2024/).

## Getting started

### Prerequisites

- Python 3.10
- [Python Poetry](https://python-poetry.org/)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [FFmpeg](https://ffmpeg.org/)

Using `brew` package manager as an example:

```shell
# Install system dependencies
brew install python@3.10 ffmpeg tesseract pipx
# Install poetry
pipx ensurepath
pipx install poetry

# Install project dependencies
poetry install
```

The virtual environment will be created locally in the `.venv` directory.

> [!NOTE]
> PyTorch with CUDA support will be only be installed on Linux environments.

## Usage

To activate the Python virtual environment, run the following command:

```sh
poetry shell
```

### Web App

To start the server, run the following command:

```sh
python main.py
```

To start the React application, run the following commands:

```sh
cd web_app
npm run dev
```

### Command Line Interface (CLI)

The CLI will generate all questions and the filtered video clips (used for our human evaluation).

```sh
python cli.py \
  --video path/to/video/file.mp4 \
  --similarity_threshold 0 \
  --output_dir_path path/to/output/directory
```

This will save the questions and all video clips to `path/to/output/directory`.

To filter the generated questions using the lecture slides (from the video), you
can provide a similarity threshold and a retention rate (filtering) threshold:

```sh
# If no threshold is given, the default (0.5) is used for both
python cli.py \
  --video path/to/video/file.mp4 \
  --similarity_threshold 0.6 \
  --filtering_threshold 0.4 \
  --output_dir_path path/to/output/directory
```

This will save only the video clips associated with the questions that have a similarity score greater than `0.6` and a retention rate greater than `0.4`.

## Scripts

See [scripts](/scripts/README.md) directory for our training and evaluation scripts.
