def build_chunks(files: list[str]) -> list[dict[str, object]]:
    return [
        {
            "chunk_id": f"chunk-{index + 1}",
            "file_path": file_path,
            "symbol_name": file_path.rsplit("/", 1)[-1],
            "start_line": 1,
            "end_line": 40,
        }
        for index, file_path in enumerate(files)
    ]
