# ---------------------------
# Chart - bar or points
# ---------------------------

# Default settings for Bar object
DEFAULT_CHART = { "x": 0, "y": 0, "w": 160, "h": 40, # 'pixels' top-left coords and width, height.
                "step": 1,             # 'pixels': how many pixels to step in x direction for next()
                "time_scale": 0.1,      # 'seconds per pixel' x-scale for Bar add_time(timestamp, height_pixels )
                "bar_width": 1,        # 'pixels', width of value column
                "point_height": 2,  # 'pixels', will display point of this height, not column to x-axis
                "cursor_width": 4,     # 'pixels', width of scrolling cursor
                "fg_color": [ 0xFF, 0xE0 ],    # yellow 565 RGB
                "bg_color": [ 0x00, 0x1F ],    # blue 565 RGB
                "cursor_color": [ 0x00, 0x00 ] # black 565 RGB
              }

# Draw a bar chart across the LCD
# For each value will draw a vertical bar plus a blank vertical margin to the right of it, as the
# use-case is expected to be a horizontal scroll of new bars.
class Chart(object):

    # Initialization for bar object
    def __init__(self, lcd, config = None):

        self.lcd = lcd

        if config is None:
            self.setting = DEFAULT_CHART
        else:
            self.setting = config

        self.prev_time = None # will hold timestamp of previous add_time() value
        self.prev_x = None    # will hold x offset (pixels) for previous add_time() value

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
        bg = self.setting["bg_color"]
        fg = self.setting["fg_color"]
        bar_width = self.setting["bar_width"]
        cursor_width = self.setting["cursor_width"]

        # make short horizontal stripe of bytes for cursor
        cursor_bytes = self.setting["cursor_color"] * cursor_width

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
            elif self.setting["point_height"] is None:
                pixelbytes.extend(bar_bytes)
            else:
                if height - row > by - self.setting["point_height"]:
                    pixelbytes.extend(bar_bytes)
                else:
                    pixelbytes.extend(blank_bytes)

        return pixelbytes


    # Clear the bar to all black
    def clear(self):
        # Build list of required number of bytes (2 bytes = 1 pixel in 565 RGB)
        pixelbytes = [ 0x00 ] * 2 * self.setting["w"] * self.setting["h"]
        self.lcd.set_window( self.setting["x"], self.setting["y"], self.setting["w"], self.setting["h"] )
        self.lcd.send_data(pixelbytes)

    # Display an image in the bar.
    # It must be exactly chart w x h
    def display(self, img):
        self.lcd.display_window( img,
                            self.setting["x"],
                            self.setting["y"],
                            self.setting["w"],
                            self.setting["h"]
                          )

    # Add a column (or point) to the chart, given the 'bx' offset and 'by' value.
    # We set a window area for just this new column, and fill it with pixels
    def add(self, bx, by):
        area_width = self.setting["bar_width"]+self.setting["cursor_width"]
        # Do nothing if added bar would overspill area
        if bx + area_width > self.setting["w"]:
            return

        # Define a small window to contain just this column
        # Note these x,y offsets are for the *LCD* not just the barchart area
        x1 = self.setting["x"] + bx
        y1 = self.setting["y"]
        self.lcd.set_window( x1, y1, area_width, self.setting["h"] )

        # Build a list containing all the pixelbytes
        pixelbytes = self.make_area(area_width, self.setting["h"], by)

        # Send the pixelbytes to the LCD
        self.lcd.send_data(pixelbytes)

    # 'Samples' on x-axis Add an incremental column and shift
    def next(self, by):
        # Add bar to display
        self.add(self.next_bx, by)
        # Increment the position for the next bar
        self.next_bx = (self.next_bx + self.setting["step"]) % self.setting["w"]

    # Add a column (or point) to the chart, given the timestamp and 'by' value
    def add_time(ts, by):
        # If this is the first value on the chart, start at x offset = 0.
        if self.prev_x is None:
            self.prev_x = 0
            self.prev_ts = ts
            self.add(0, by)

        # We will fill in an area from the previous point to this one.
        else:
            # calculate x-adjustment for new value as offset from previous point
            x_adj = math.floor((ts - self.prev_ts) / self.setting["time_scale"] + 0.5)

            # convert to absolute x position of new point, even though it might overspill bar area
            x_offset = self.prev_x + x_adj

            # if new point is off end of bar chart, fill columns after prev_x with bg_color
            # Note coordinates for set_windor are LCD coords, not just within chart area
            if x_offset > self.setting["w"]:
                x = self.setting["x"] + self.prev_x + self.setting["bar_width"]
                w = self.setting["w"] - self.prev_x - self.setting["bar_width"]

                self.lcd.set_window( x, self.setting["y"], w, self.setting["h"] )

                pixelbytes = self.setting["bg_color"] * (x2 - x1) *  h

                self.lcd.send_data(pixelbytes)
