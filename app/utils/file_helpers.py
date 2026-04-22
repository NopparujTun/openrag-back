ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".csv"}

def is_allowed_file(filename: str) -> bool:
    """Checks if the file extension is allowed."""
    extension = "." + filename.split(".")[-1].lower() if "." in filename else ""
    return extension in ALLOWED_EXTENSIONS
