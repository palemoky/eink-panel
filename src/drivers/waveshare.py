import importlib
import logging

from PIL import Image

logger = logging.getLogger(__name__)


class WaveshareEPDDriver:
    def __init__(self, model_name: str, use_grayscale: bool = False):
        """
        初始化 Waveshare 驱动适配器
        :param model_name: 驱动模块名称，例如 'epd7in5_V2'
        :param use_grayscale: 是否使用 4 级灰度模式
        """
        try:
            # 动态导入 src.lib.waveshare_epd.{model_name}
            module_path = f"src.lib.waveshare_epd.{model_name}"
            self.epd_module = importlib.import_module(module_path)

            # 实例化 EPD 类
            self.epd = self.epd_module.EPD()
            self.width = self.epd.width
            self.height = self.epd.height
            self.use_grayscale = use_grayscale

            # Check if grayscale is supported
            if use_grayscale:
                if not hasattr(self.epd, "init_4Gray"):
                    logger.warning(
                        f"Grayscale mode requested but not supported by {model_name}, "
                        "falling back to black/white mode"
                    )
                    self.use_grayscale = False
                else:
                    logger.info(
                        f"Loaded Waveshare driver: {model_name} ({self.width}x{self.height}) - 4-Gray Mode"
                    )
            else:
                logger.info(
                    f"Loaded Waveshare driver: {model_name} ({self.width}x{self.height}) - B/W Mode"
                )

        except ImportError as e:
            logger.error(f"Failed to load Waveshare driver '{model_name}': {e}")
            raise
        except AttributeError as e:
            logger.error(
                f"Driver '{model_name}' does not have expected EPD class or attributes: {e}"
            )
            raise

    def init(self, fast: bool = False) -> None:
        """Initialize the display.

        Args:
            fast: If True, use fast refresh mode (less flashing but may have ghosting).
                  If False, use full refresh mode (more flashing but better quality).
                  Note: Fast mode is not available in grayscale mode.
        """
        if self.use_grayscale:
            logger.debug("Initializing display in 4-gray mode")
            self.epd.init_4Gray()
        elif fast and hasattr(self.epd, "init_fast"):
            logger.debug("Using fast refresh mode")
            self.epd.init_fast()
        else:
            logger.debug("Using full refresh mode")
            self.epd.init()

    def clear(self) -> None:
        self.epd.Clear()

    def sleep(self) -> None:
        self.epd.sleep()

    def getbuffer(self, image: Image.Image):
        """Convert PIL Image to buffer format for the display.

        Args:
            image: PIL Image to convert (mode "L" for grayscale, "1" for B/W)

        Returns:
            Buffer in the format expected by the display
        """
        # If image is explicitly B/W ("1"), use standard getbuffer
        if image.mode == "1":
            return self.epd.getbuffer(image)

        # If image is grayscale ("L") and driver supports it, use grayscale buffer
        if self.use_grayscale and hasattr(self.epd, "getbuffer_4Gray"):
            return self.epd.getbuffer_4Gray(image)

        # Fallback: convert to B/W buffer
        return self.epd.getbuffer(image)

    def display(self, image: Image.Image) -> None:
        """Display an image on the e-ink screen.

        Args:
            image: PIL Image to display (mode "L" for grayscale, "1" for B/W)
        """
        if self.use_grayscale and hasattr(self.epd, "display_4Gray"):
            buffer = self.epd.getbuffer_4Gray(image)
            self.epd.display_4Gray(buffer)
        else:
            buffer = self.epd.getbuffer(image)
            self.epd.display(buffer)

    def display_partial_buffer(
        self, buffer, x_start: int, y_start: int, x_end: int, y_end: int
    ) -> None:
        """Perform partial display update using a pre-converted buffer.

        This is a low-level method that directly calls the Waveshare display_Partial method.
        Use this when you've already converted the image to a buffer for better performance.

        Args:
            buffer: Pre-converted buffer from getbuffer() - MUST be full-size image buffer
            x_start: X coordinate of top-left corner
            y_start: Y coordinate of top-left corner
            x_end: X coordinate of bottom-right corner (not width!)
            y_end: Y coordinate of bottom-right corner (not height!)
        """
        if hasattr(self.epd, "display_Partial"):
            # Extract the partial region from the full buffer
            # The Waveshare display_Partial expects a buffer containing only the region data
            # Buffer format: 1 bit per pixel, packed into bytes (8 pixels per byte)

            # Align X coordinates to 8-pixel boundaries (required by hardware)
            x_start_aligned = (x_start // 8) * 8
            x_end_aligned = ((x_end + 7) // 8) * 8

            width_bytes = (x_end_aligned - x_start_aligned) // 8

            # Extract the region from the full buffer
            partial_buffer = bytearray()
            full_width_bytes = self.epd.width // 8

            for y in range(y_start, y_end):
                # Calculate the starting byte position in the full buffer for this row
                row_start = y * full_width_bytes + (x_start_aligned // 8)
                row_end = row_start + width_bytes
                partial_buffer.extend(buffer[row_start:row_end])

            logger.debug(
                f"Partial refresh: region ({x_start},{y_start})-({x_end},{y_end}), "
                f"aligned ({x_start_aligned},{y_start})-({x_end_aligned},{y_end}), "
                f"buffer size: {len(partial_buffer)} bytes"
            )

            self.epd.display_Partial(partial_buffer, x_start_aligned, y_start, x_end_aligned, y_end)
        else:
            logger.warning(f"Partial display not supported for {self.epd.__class__.__name__}")

    def init_part(self) -> None:
        """Initialize partial refresh mode if supported."""
        if hasattr(self.epd, "init_part"):
            self.epd.init_part()
        else:
            logger.warning(
                f"Partial refresh initialization not supported for {self.epd.__class__.__name__}"
            )

    def display_partial(self, image: Image.Image, x: int, y: int, w: int, h: int) -> None:
        """Display a partial region of the screen (high-level API).

        This is the standard interface that accepts a PIL Image and automatically
        converts it to a buffer. Use this for convenience.

        Args:
            image: PIL Image to display (must be FULL SIZE, e.g., 800x480)
            x: X coordinate of top-left corner of region to update
            y: Y coordinate of top-left corner of region to update
            w: Width of the region to update
            h: Height of the region to update
        """
        if hasattr(self.epd, "display_Partial"):
            # EPD expects full-size image buffer and end coordinates
            buffer = self.epd.getbuffer(image)
            self.epd.display_Partial(buffer, x, y, x + w, y + h)
        else:
            # Fallback to full display if partial not supported
            logger.warning(
                f"Partial display not supported for {self.epd.__class__.__name__}, using full display"
            )
            self.display(image)
