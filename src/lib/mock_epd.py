import logging

logger = logging.getLogger(__name__)

class MockEPD:
    """Mock EPD driver for testing on non-Raspberry Pi environments."""
    width, height = 800, 480

    def init(self):
        logger.info("Mock EPD: init")

    def Clear(self):
        logger.info("Mock EPD: Clear")

    def display(self, buf):
        logger.info("Mock EPD: display")

    def getbuffer(self, img):
        return None

    def sleep(self):
        logger.info("Mock EPD: sleep")
