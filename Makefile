PYTHON := python3
LATEX := pdflatex
LATEX_DIR := docs
LATEX_OPTS := -shell-escape  # Required for minted package

.PHONY: install record record-words record-new clean help syllables compose play docs clean-docs init record-with-syllables

install:
	$(PYTHON) -m pip install -r requirements.txt

init:
	@echo "Initializing dataset directory structure..."
	@mkdir -p dataset
	@if [ ! -f words.txt ]; then \
		echo "Creating empty words.txt file..."; \
		touch words.txt; \
	fi
	@echo "Creating example metadata..."
	@echo "Project structure initialized successfully!"
	@echo "\nDirectory structure created:"
	@echo "  dataset/     - For recorded audio files"
	@echo "  words.txt    - Add your words here"
	@echo "\nNext steps:"
	@echo "1. Add words to words.txt"
	@echo "2. Run 'make record-words' to start recording"
	@echo "3. Run 'make syllables' to extract syllables"

record:
	$(PYTHON) -m src.dataset_generator.cli_dataset_generator

record-words:
	$(PYTHON) -m src.dataset_generator.cli_dataset_generator --words words.txt

record-new:
	$(PYTHON) -m src.dataset_generator.cli_dataset_generator --words words.txt --skip-recorded

record-with-syllables:
	$(PYTHON) -m src.dataset_generator.syllable_extractor
	$(PYTHON) -m src.dataset_generator.cli_dataset_generator --words dataset/unique_syllables.txt --syllables-mode

syllables:
	$(PYTHON) -m src.dataset_generator.syllable_extractor

compose:
	$(PYTHON) -m src.text_composer --words 5

play:
	$(PYTHON) -m src.text_composer --text "кожен день ми стикаємося з безліччю"

play-and-save:
	$(PYTHON) -m src.text_composer --text "кожен день ми стикаємося з безліччю" --save

clean:
	find dataset -name "*.wav" -delete
	find dataset -name "*_metadata.json" -delete
	rm -f dataset/unique_syllables.txt dataset/syllables_stats.json

help:
	@echo "Usage: make <target>"
	@echo "Targets:"
	@echo "  init         Initialize project directory structure"
	@echo "  install      Install dependencies"
	@echo "  record       Record audio in free mode"
	@echo "  record-words Record audio for all words in words.txt"
	@echo "  record-new   Record only new words, skip already recorded ones"
	@echo "  record-with-syllables Record syllables from words.txt"
	@echo "  syllables    Extract unique syllables from words.txt"
	@echo "  compose      Generate and play random text using recorded words"
	@echo "  play         Play specific text using recorded words"
	@echo "  play-and-save Play specific text using recorded words and save the output"
	@echo "  clean        Clean up dataset"