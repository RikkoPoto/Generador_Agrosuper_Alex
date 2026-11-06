# Build v0.2
Ultimo bug descubierto: La compilacion funciona correctamente, sin embargo la ingeneria en la conversion del ppt_gen no hace que pase los assets

## revisar el compilado y que la imagen corra bien y si atao

pip install pyinstaller
python -m PyInstaller --noconsole --onefile --name="Generador_Agrosuper_Alex" --add-data "assets;assets" main.py