# Louriña Films 0.4.0 — versión previa

## Cambios

- Identidade Louriña Films completada: paquete e executábel `lourihna_films`, distribución `lourihna-films` e contorno `LOURIHNA_FILMS`.
- Guía EIDO conservada sen cambios, cabeceiras e contratos públicos en inglés, anotacións e formato Ruff. Os nomes esixidos por Qt/QML mantéñense.
- Benvida co logotipo actual, mínimo de tres segundos medidos desde o primeiro fotograma e inicialización de datos en segundo plano.
- Migración SQLite sen sobrescribir o destino nin borrar os orixinais.
- Licenza MIT para o código propio e avisos de terceiros conservados.
- README en galego e compilacións automatizadas para Windows e Linux.

## Comprobacións

- 162 probas locais superadas, incluídas as rutas de inicio rápido, lento, erro, peche e migración.
- Ruff: lint e formato correctos; sintaxe, imports e contratos públicos revisados.
- Interface QML real con 2.000 entradas: sen erros QML; paginación e posición do scroll conservadas.
- Controis reais: pausa, avance, volume, silencio, pantalla completa, parada e posición gardada.
- Captura real da benvida; mínimo medido de 3.059 ms.
- O verificador empaquetado comproba o mínimo de 3.000 ms, arranque, reprodución dun vídeo de proba, ciclo do navegador, integridade SQLite e preferencias tras reiniciar.
- Linux x86_64: construído e verificado nun runner Ubuntu 24.04 con Xvfb. Windows x86_64: verificado localmente; consulta tamén o workflow da versión.

## Descargas

- `lourihna-films-0.4.0-windows-x86_64-setup.exe`: instalador por usuario para Windows x86_64.
- `lourihna-films-0.4.0-linux-x86_64.tar.gz`: paquete portable Linux con `install.sh`; base Ubuntu 24.04 / glibc 2.39.
- `lourihna-films-0.4.0-source.zip`: código fonte na raíz. Non é un instalador.
- `SHA256SUMS.txt`: sumas de verificación dos ficheiros publicados.

## Limitacións

É unha versión previa, non unha certificación de compatibilidade con todas as versións de Windows ou distribucións Linux. Windows 10 1809 é o requisito mínimo declarado polo empaquetado, pero non se probou aquí ese sistema. Non hai ARM nativo nin firma comercial do instalador. Linux precisa as bibliotecas de Qt indicadas no README; non se probou en todos os escritorios.

As probas usan vídeos locais e provedores simulados cando corresponde. Non garanten dispoñibilidade de películas nin funcionamento continuo dos servizos externos. As credenciais persoais e os modelos de tradución non se inclúen nos paquetes.

As únicas referencias literais á identidade anterior no código actual son as tres constantes de `core/compatibility.py`. O historial Git e as copias locais arquivadas consérvanse. O informe completo está en `docs/EIDO-MIGRATION.md`.
