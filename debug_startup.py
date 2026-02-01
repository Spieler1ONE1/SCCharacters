
try:
    print("Attempting import...")
    from src.ui.dialogs.news_reader import NewsReaderDialog
    print("Import failed? No, success.")
except Exception as e:
    print(f"Import Error: {e}")
    import traceback
    traceback.print_exc()
