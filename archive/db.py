# import datetime
# import hashlib
# import logging
# from pathlib import Path

# from pydal import DAL, Field

# log = logging.getLogger(__name__)
# dbfolder = Path(__file__).parent.parent.parent / "data"

# db = DAL("sqlite://storage.sqlite", folder=dbfolder)

# db.define_table(
#     "ward",
#     Field("authority"),
#     Field("wardname"),
#     Field("year", "integer"),
#     Field("geometry"),
#     Field(
#         "md5",
#         length=64,
#         unique=True,
#         writable=False,
#         readdable=False,
#         compute=lambda row: hashlib.md5(
#             f"{row.authority}:{row.wardname}:{row.year}".encode()
#         ).hexdigest(),
#     ),
# )
# db.define_table(
#     "results",
#     Field("ward", "reference ward"),
#     Field("party"),
#     Field("votes", "integer"),
# )
