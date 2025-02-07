def load_from_file(filename, default_list=None):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return [line.strip() for line in file.readlines()]
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return default_list or []