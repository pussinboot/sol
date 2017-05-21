from osc import OscServer
import time

if __name__ == '__main__':
    test_server = OscServer()
    test_server.dispatcher._default_handler = print
    test_server.start()
    while True:
        try:
            time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            print("exiting...")
            test_server.stop()
            break