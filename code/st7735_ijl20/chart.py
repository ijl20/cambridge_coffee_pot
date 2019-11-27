# ---------------------------
# Chart - bar or points
# ---------------------------

"""
Creates a bar chart or point plot across LCD,
with samples or time on the x-axis.

Is designed to be efficient when adding one point at a time by updating the minimum screen area.

Note that variables (x,y) generally refer to DISPLAY AREA coordinates (i.e. within 160x128)
while variables (bx,by) refer to coordinates within the CHART AREA.
"""

import math

# Default settings for Bar object
DEFAULT_CHART = { "x": 0, "y": 0, "w": 160, "h": 40, # 'pixels' top-left coords and width, height.
                "step": 1,             # 'pixels': how many pixels to step in x direction for next()
                "time_scale": 0.1,      # 'seconds per pixel' x-scale for Bar add_time(timestamp, height_pixels )
                "bar_width": 1,        # 'pixels', width of value column
                "point_height": None,  # 'pixels', will display point of this height, not column to x-axis
                "cursor_width": 2,     # 'pixels', width of scrolling cursor
                "fg_color": [ 0xFF, 0xE0 ],    # yellow 565 RGB
                "bg_color": [ 0x00, 0x1F ],    # blue 565 RGB
                "cursor_color": [ 0x00, 0x00 ] # black 565 RGB
              }

# Draw a bar chart across the LCD
# For each value will draw a vertical bar plus a blank vertical margin to the right of it, as the
# use-case is expected to be a horizontal scroll of new bars.
class Chart(object):

    # Initialization for bar object
    def __init__(self, lcd, settings = None):

        self.lcd = lcd

        if settings is None:
            self.settings = DEFAULT_CHART
        else:
            self.settings = settings

        self.prev_time = None # will hold timestamp of previous add_time() value
        self.prev_bx = None    # will hold x offset (pixels) for previous add_time() value

        # Initial x offset for next() column
        self.next_bx = 0

    # Build a list of RGB 565 color byte pairs designed to fill an area of the chart
    # e.g with width = 12, height = 7, bar_width = 2, cursor_width = 3, point_height = 2, by (value) = 4
    # if b = bg_color, F = fg_color and C = cursor_color, each pixel as *pair* of bytes
    # b b b b b b b b b b C C C
    # b b b b b b b b b b C C C
    # b b b b b b b b b b C C C
    # b b b b b b b b F F C C C
    # b b b b b b b b F F C C C
    # b b b b b b b b b b C C C
    # b b b b b b b b b b C C C
    # Entire array is returned as list of bytes, left-to-right, top-to-bottom.
    def make_area(self, width, height, by):
        # convenient short names
        bg = self.settings["bg_color"]
        fg = self.settings["fg_color"]
        bar_width = self.settings["bar_width"]
        cursor_width = self.settings["cursor_width"]

        # make short horizontal stripe of bytes for cursor
        cursor_bytes = self.settings["cursor_color"] * cursor_width

        # make horizontal stripe for 'blank' rows (i.e. above column or below point)
        # i.e. background bytes followed by cursor bytes.
        blank_bytes = bg * (width - cursor_width)
        blank_bytes.extend(cursor_bytes)

        # make horizontal stripe of color bytes for column or point
        # i.e. background bytes followed by foreground bytes followed by cursor bytes.
        bar_bytes = bg * (width - bar_width - cursor_width)
        bar_bytes.extend(fg * bar_width)
        bar_bytes.extend(cursor_bytes)

        # iterate rows of area from top to bottom,
        # appending appropriate list of pixels for each row
        pixelbytes = []
        for row in range(height):
            if height - row > by:
                pixelbytes.extend(blank_bytes)
            elif self.settings["point_height"] is None:
                pixelbytes.extend(bar_bytes)
            else:
                if height - row > by - self.settings["point_height"]:
                    pixelbytes.extend(bar_bytes)
                else:
                    pixelbytes.extend(blank_bytes)

        return pixelbytes


    # Clear the chart from bx to bx+w with bg_color
    # Defaults to clearing whole chart area
    def clear(self, cx=0, cw=None):
        if cw is None:
            cw = self.settings["w"]

        # Convert chart bx coordinate to screen x coordinate:
        x = self.settings["x"] + cx

        # Build list of required number of bytes (2 bytes = 1 pixel in 565 RGB)
        pixelbytes = self.settings["bg_color"] * cw * self.settings["h"]
        self.lcd.set_window( x, self.settings["y"], cw, self.settings["h"] )
        self.lcd.send_data(pixelbytes)

    # Display an image in the bar.
    # It must be exactly chart w x h
    def display(self, img):
        self.lcd.display_window( img,
                            self.settings["x"],
                            self.settings["y"],
                            self.settings["w"],
                            self.settings["h"]
                          )

    # Add a column (or point) to the chart, given the 'bx' offset and 'by' value.
    # We set a window area for just this new column, and fill it with pixels
    def add(self, bx, by):
        area_width = self.settings["bar_width"]+self.settings["cursor_width"]
        # Do nothing if added bar would overspill area
        if bx + area_width > self.settings["w"]:
            return

        # Define a small window to contain just this column
        # Note these x,y offsets are for the *LCD* not just the barchart area
        x1 = self.settings["x"] + bx
        y1 = self.settings["y"]
        self.lcd.set_window( x1, y1, area_width, self.settings["h"] )

        # Build a list containing all the pixelbytes
        pixelbytes = self.make_area(area_width, self.settings["h"], by)

        # Send the pixelbytes to the LCD
        self.lcd.send_data(pixelbytes)

    # 'Samples' on x-axis Add an incremental column and shift
    def next(self, by):
        # Add bar to display
        self.add(self.next_bx, by)
        # Increment the position for the next bar
        self.next_bx = (self.next_bx + self.settings["step"]) % self.settings["w"]

    # Add a column (or point) to the chart, given the timestamp and 'by' value
    def add_time(self, ts, by):
        # If this is the first value on the chart, start at x offset = 0.
        if self.prev_bx is None:
            bx = 0

        # We will fill in an area from the previous point to this one.
        else:
            # calculate x-adjustment for new value as offset from previous point
            x_adj = math.floor((ts - self.prev_ts) / self.settings["time_scale"] + 0.5)

            # convert to absolute x position of new point, even though it might overspill bar area
            bx = self.prev_bx + x_adj

            # we now need to clear areas, and add new point
            if bx < self.settings["w"]:
                # New point is a simple follow-on from prev_bx within chart width, we
                # clear from the prev_bx to the new bx and draw new point at bx.
                cx = self.prev_bx + self.settings["bar_width"]
                cw = bx - self.prev_bx - self.settings["bar_width"]
                self.clear(cx,cw)
            else:
                # New point has wrapped off end of chart
                if bx - self.settings["w"] < self.prev_bx:
                    # New point is beyond w but less than a full chart width further.
                    # so we clear from prev_bx + bar_width to w
                    cx = self.prev_bx + self.settings["bar_width"]
                    cw = self.settings["w"] - self.prev_bx + self.settings["bar_width"]
                    self.clear(cx,cw)
                    bx = bx - self.settings["w"]
                else:
                    # New point is a whole chart width wrapped around from previous point.
                    # So we clear from bx % chart width to w
                    bx = bx % self.settings["w"]
                    cx = bx + self.settings["bar_width"]
                    cw = self.settings["w"] - bx - self.settings["bar_width"]
                    self.clear(cx,cw)

                # clear from left edge up to wrapped point
                self.clear(0,bx)

        # add point
        self.add(bx,by)

        self.prev_bx = bx
        self.prev_ts = ts

