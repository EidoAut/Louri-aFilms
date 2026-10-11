# Louriña Films 0.5.0 — preparada para publicación

## Novidades

- Portada cinematográfica, filas panorámicas, tarxetas ampliadas e fichas modais.
- Navegación con teclado e conservación da posición ao pechar unha ficha.
- Melloras de fluidez: actualización por campo e reutilización de imaxes.
- Selector de saída de audio no reprodutor nativo, con modo automático e HDMI
  cando o televisor está dispoñible no sistema.
- Borrado selectivo de buscas e reproducións desde o menú principal, con
  confirmación. Conserva favoritos, colección e axustes.
- Correccións de arranque con credenciais malformadas, reanudación e detección
  de progreso despois de retroceder nun vídeo web.

## Paquetes preparados

- `lourihna-films-0.5.0-windows-x86_64-portable.zip`
- `lourihna-films-0.5.0-linux-x86_64.tar.gz`
- `lourihna-films-0.5.0-source.zip`
- `SHA256SUMS.txt`

GitHub Actions tamén permite crear un instalador Windows con Inno Setup. Non
forma parte da entrega local ata que se xere expresamente. Os paquetes non
inclúen claves, contas, bases de datos nin modelos de tradución descargados.

## Requisitos e límites

Windows x86_64, validado localmente en Windows 11. Linux x86_64 cunha base
compatible con Ubuntu 24.04 e glibc 2.39. Consulta `BUILD-INFO.json` para ver as
dependencias exactas do paquete. Non hai compilación ARM.

## Comprobacións realizadas

- Windows 11: 183 probas superadas; Ruff e formato correctos.
- Linux Ubuntu 24.04 en contorno illado sobre WSL2: 182 probas superadas e
  unha omitida por ser específica de Windows; Ruff e formato correctos.
- Ambos os executables: arranque, reprodución dun vídeo local de proba,
  ciclo do navegador integrado, integridade SQLite e reinicio con preferencias.
  En Linux utilizouse Xvfb, sen escritorio nin saída de audio físicos.
- Exportación de fontes: rexeitamento de datos privados mesmo se están
  engadidos a Git; comprobación de contido e integridade dos arquivos finais.

A primeira comprobación de reprodución Windows fallou durante a compilación
simultánea; as dúas repeticións posteriores completáronse correctamente. A proba
ten unha espera fixa e non mide o rendemento en todos os equipos.

Os catálogos e os vídeos dependen dos provedores. As previsualizacións usan
imaxes estáticas cando non hai tráiler verificado. A proba automatizada de audio
non substitúe comprobar un televisor HDMI físico. A validación Linux sen pantalla
real non certifica todos os escritorios, controladores nin dispositivos de audio.

Esta preparación non publica automaticamente a versión en GitHub nin altera os
perfís dos usuarios que instalen unha actualización.
