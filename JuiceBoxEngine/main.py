from scripts.juiceBoxEngineServer import JuiceBoxEngineServer
from scripts.juiceShopManager import JuiceShopManager
from scripts.rootTheBoxManager import RootTheBoxManager
from scripts.utils.config import JuiceShopConfig, RTBConfig

if __name__ == "__main__":
    # Se instancian los managers
    rtb = RootTheBoxManager(RTBConfig())  # Root the Box
    js = JuiceShopManager(JuiceShopConfig())  # Juice Shop

    # Se instancia el motor:
    jb_server = JuiceBoxEngineServer(js, rtb)
