from rom_hub_sdk import FetchFile, FetchPlan, ImportProvider


class Importer(ImportProvider):
    def __init__(self, ctx):
        self.ctx = ctx

    def plan(self, result) -> FetchPlan:
        filename = result.extra.get("filename") or f"{result.title}.7z"
        return FetchPlan(
            platform=result.platform or "",
            collection="LoLSuite",
            files=[FetchFile(url=result.source_id, filename=filename, size_bytes=result.size_bytes)],
        )
