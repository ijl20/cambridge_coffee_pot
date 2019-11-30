# Various utility functions

# ---------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------
# list_to_string() function
# 'pretty formats' a list for printing, i.e. '[ <value>, <value>, ...]'
# The actual values can be formatted with a format string, default '{}'
# e.g. '{:.3f}' will format number as a float with 3 decimal places.
# ---------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------

# Convert [1,2,3] to "1, 2, 3" using optional format string e.g "{:.1f}"
def list_to_string(input_list, format_string="{}"):
    output_string = ""

    first_separator = ""

    separator = ", " ## added *before* each element except first

    first_added = False # flag to detect whether we are currently adding first element

    for element in input_list:
        if not first_added:
            output_string = output_string + first_separator
            first_added = True
        else:
            output_string = output_string + separator

        # add the formatted element
        output_string = output_string + format_string.format(element)

    return output_string
