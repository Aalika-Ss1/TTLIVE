import csv
import io
import zipfile
from datetime import datetime, timezone
from xml.sax.saxutils import escape

from sqlalchemy.orm import Session

from tournament_os.application.leaderboards import LeaderboardQueryService


LEADERBOARD_EXPORT_FIELDS = ["rank", "display_name", "group_name", "total_points", "games_played"]


class ExportService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.leaderboard_service = LeaderboardQueryService(session)

    def _leaderboard_rows(self, tournament_id: str) -> list[dict[str, object]]:
        records = self.leaderboard_service.public_leaderboard(tournament_id)
        return [
            {
                "rank": record.get("rank"),
                "display_name": record.get("display_name"),
                "group_name": record.get("group_name") or "",
                "total_points": record.get("total_points"),
                "games_played": record.get("games_played"),
            }
            for record in records
        ]

    def export_leaderboard_csv(self, tournament_id: str) -> str:
        """
        Exports the public leaderboard as a CSV string.
        Only includes approved/final/corrected scores and no private data.
        """
        rows = self._leaderboard_rows(tournament_id)
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=LEADERBOARD_EXPORT_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue()

    def export_leaderboard_xlsx(self, tournament_id: str) -> bytes:
        rows = self._leaderboard_rows(tournament_id)
        worksheet_xml = self._build_worksheet_xml([LEADERBOARD_EXPORT_FIELDS, *rows])
        created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

        parts = {
            "[Content_Types].xml": self._content_types_xml(),
            "_rels/.rels": self._root_relationships_xml(),
            "docProps/app.xml": self._app_properties_xml(),
            "docProps/core.xml": self._core_properties_xml(created_at),
            "xl/workbook.xml": self._workbook_xml(),
            "xl/_rels/workbook.xml.rels": self._workbook_relationships_xml(),
            "xl/styles.xml": self._styles_xml(),
            "xl/worksheets/sheet1.xml": worksheet_xml,
        }

        output = io.BytesIO()
        with zipfile.ZipFile(output, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path, content in parts.items():
                archive.writestr(path, content)
        return output.getvalue()

    def _build_worksheet_xml(self, rows: list[object]) -> str:
        row_xml = []
        for row_number, row in enumerate(rows, start=1):
            values = row if isinstance(row, list) else [row.get(field, "") for field in LEADERBOARD_EXPORT_FIELDS]
            cells = []
            for column_number, value in enumerate(values, start=1):
                cell_ref = f"{self._column_name(column_number)}{row_number}"
                cells.append(
                    f'<c r="{cell_ref}" t="inlineStr"><is><t>{escape(str(value if value is not None else ""))}</t></is></c>'
                )
            row_xml.append(f'<row r="{row_number}">{"".join(cells)}</row>')
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            f'<sheetData>{"".join(row_xml)}</sheetData>'
            "</worksheet>"
        )

    def _column_name(self, column_number: int) -> str:
        name = ""
        while column_number:
            column_number, remainder = divmod(column_number - 1, 26)
            name = chr(65 + remainder) + name
        return name

    def _content_types_xml(self) -> str:
        return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>"""

    def _root_relationships_xml(self) -> str:
        return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""

    def _workbook_xml(self) -> str:
        return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Leaderboard" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>"""

    def _workbook_relationships_xml(self) -> str:
        return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

    def _styles_xml(self) -> str:
        return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>
  <fills count="1"><fill><patternFill patternType="none"/></fill></fills>
  <borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>
  <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>"""

    def _app_properties_xml(self) -> str:
        return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Tournament OS</Application>
</Properties>"""

    def _core_properties_xml(self, created_at: str) -> str:
        return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:creator>Tournament OS</dc:creator>
  <cp:lastModifiedBy>Tournament OS</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{created_at}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{created_at}</dcterms:modified>
</cp:coreProperties>"""
