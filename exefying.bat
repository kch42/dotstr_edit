@echo off
REM  Exefying the script...

python.exe -OO mkexe.py py2exe

REM  Uncomment next line, if you do not want to compress...
REM  goto end

REM  recompress the library
cd dist\
7z.exe -aoa x library.zip -olibrary\
cd library\
7z.exe a -tzip -mx9 ..\library.zip -r
cd ..
rd library /s /q

REM  UPX-Packing
upx.exe --best *.*
:end
echo Done
