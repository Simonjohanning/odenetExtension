import dbUtils
import sqlite_to_xml
import util
import dbhandling

# establish the db
cursor, connection = dbhandling.import_sql_dump(
    host="localhost",
    user="sim",
    password="developmentPassw0rd",
    database="open_thesaurus",
    dump_file_path="openthesaurus_dump.sql",
    quiet=True
)

#print(dbUtils.findSynsetForWord(connection, 'Artilleriebeschuss'))
sqlite_to_xml.generate_xml_data(connection)

#sqlite_to_xml.generate_xml_data('./openthesaurus_dump_250224.sql')
#util.extract_tarball('./openthesaurus_dump_250224.tar.bz2')