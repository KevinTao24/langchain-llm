make format:
	find . -name "__pycache__" -exec rm -rf {} \;
	isort .
	black .