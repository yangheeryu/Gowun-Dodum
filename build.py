from glyphsLib.cli import main
from fontTools.ttLib import TTFont, newTable
from pathlib import Path
import shutil, os, glob
import ufo2ft
import ufoLib2
import multiprocessing
import multiprocessing.pool


path = Path("sources")

#Converting from Glyphs to UFO
print ("[Gowun Dotum] Converting to UFO")
main(("glyphs2ufo", "sources/GowunDodum.glyphs", "--write-public-skip-export-glyphs", "--propagate-anchors"))

def DSIG_modification(font:TTFont):
    font["DSIG"] = newTable("DSIG")     #need that stub dsig
    font["DSIG"].ulVersion = 1
    font["DSIG"].usFlag = 0
    font["DSIG"].usNumSigs = 0
    font["DSIG"].signatureRecords = []

def GASP_set(font:TTFont):
    if "gasp" not in font:
        font["gasp"] = newTable("gasp")
        font["gasp"].gaspRange = {}
    if font["gasp"].gaspRange != {65535: 0x000A}:
        font["gasp"].gaspRange = {65535: 0x000A}

def build(ufo:ufoLib2):
    source = ufoLib2.Font.open(ufo)
    source.lib['com.github.googlei18n.ufo2ft.filters'] = [
        {
         "name": "decomposeTransformedComponents",
         "pre": 1,
        },
        {
         "name": "flattenComponents",
         "pre": 1,
        },
     ]
    
    style_name = source.info.styleName
    family_name = str(source.info.familyName).replace(" ","")

    static_ttf = ufo2ft.compileTTF(
        source, 
        removeOverlaps=True, 
        overlapsBackend="pathops", 
        useProductionNames=True,
    )
    DSIG_modification(static_ttf)
    GASP_set(static_ttf)

    print ("[Dongle "+str(style_name).replace(" ","")+"] Saving")
    output = "fonts/ttf/"+family_name+"-"+str(style_name).replace(" ","")+".ttf"
    static_ttf.save(output)


pool = multiprocessing.pool.Pool(processes=multiprocessing.cpu_count())
processes = []

for source in path.glob("*.ufo"): # GOTTA GO FAST
    processes.append(
        pool.apply_async(
            build,
            (
                source,
            ),
        )
    )

pool.close()
pool.join()
for process in processes:
    process.get()
del processes, pool

# Cleanup

for ufo in path.glob("*.ufo"):
    shutil.rmtree(ufo)
os.remove("sources/GowunDodum.designspace")