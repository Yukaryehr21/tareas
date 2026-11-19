"""Subir y ver la imagen de un producto."""

from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from ..repository_sql import SqlProductoRepository, get_repo
from ..schemas import ProductoOut
from ..storage import TAMANO_MAXIMO, detectar_tipo, get_upload_dir

router = APIRouter(prefix="/productos", tags=["Imágenes"])

Repo = Annotated[SqlProductoRepository, Depends(get_repo)]
Carpeta = Annotated[Path, Depends(get_upload_dir)]


@router.post("/{producto_id}/imagen", response_model=ProductoOut, status_code=status.HTTP_200_OK)
def subir_imagen(
    producto_id: int,
    archivo: UploadFile,
    repo: Repo,
    carpeta: Carpeta,
) -> ProductoOut:
    if repo.get(producto_id) is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    contenido = archivo.file.read(TAMANO_MAXIMO + 1)
    if len(contenido) > TAMANO_MAXIMO:
        raise HTTPException(status_code=413, detail="El archivo supera 1 MB")

    tipo = detectar_tipo(contenido)
    if tipo is None:
        raise HTTPException(status_code=415, detail="Solo se aceptan imágenes PNG o JPEG")

    _, extension = tipo
    destino = carpeta / f"{uuid4().hex}{extension}"
    destino.write_bytes(contenido)

    producto = repo.guardar_imagen(producto_id, str(destino))
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto


@router.get("/{producto_id}/imagen")
def ver_imagen(producto_id: int, repo: Repo) -> FileResponse:
    ruta = repo.ruta_imagen(producto_id)
    if ruta is None or not Path(ruta).exists():
        raise HTTPException(status_code=404, detail="El producto no tiene imagen")
    return FileResponse(ruta)