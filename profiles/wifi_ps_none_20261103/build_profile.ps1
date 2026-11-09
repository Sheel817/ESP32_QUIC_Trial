$env:PYTHONUTF8 = '1'
$env:ESP_IDF_VERSION = '6.1.0'
$env:IDF_PATH = 'C:\esp\v6.1\esp-idf'
$env:IDF_TOOLS_PATH = 'C:\Users\newsh\.espressif'
$env:IDF_PYTHON_ENV_PATH = 'C:\Users\newsh\.espressif\python_env\idf6.1_py3.14_env'
$env:IDF_COMPONENT_CHECK_NEW_VERSION = '0'
$env:PATH = "$env:IDF_PYTHON_ENV_PATH\Scripts;C:\Espressif\tools\cmake\4.0.3\bin;C:\Espressif\tools\ninja\1.12.1;C:\Espressif\tools\riscv32-esp-elf\esp-15.2.0_20251204\riscv32-esp-elf\bin;" + $env:PATH
& "$env:IDF_PYTHON_ENV_PATH\Scripts\python.exe" "$env:IDF_PATH\tools\idf.py" -B C:/Users/newsh/Desktop/ESP32_QUIC_Trial/profiles/wifi_ps_none_20261103/build -DSDKCONFIG=C:/Users/newsh/Desktop/ESP32_QUIC_Trial/profiles/wifi_ps_none_20261103/sdkconfig -DDEMO_TRANSPORT=QUIC -DDEMO_WIFI_PS_NONE=ON -DCCACHE_ENABLE=False build
