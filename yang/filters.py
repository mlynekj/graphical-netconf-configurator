from lxml import etree as ET
from ncclient.xml_ import to_ele

# Helper module for storing basic classes for filters, from which other filters can inherit.

class GetFilter:
    def __init__(self):
        # Implemented in child classes
        pass

    def __str__(self):
        """
        This method converts the filter_xml attribute to a string using the
        ElementTree tostring method and decodes it to UTF-8.
        This is needed for dispatching RPCs with ncclient.

        Returns:
            str: The string representation of the filter_xml attribute.
        """

        return(ET.tostring(self.filter_xml).decode('utf-8'))
    

class EditconfigFilter:
    def __init__(self):
        # Implemented in child classes
        pass

    def __str__(self):
        """
        This method converts the filter_xml attribute to a string using the
        ElementTree tostring method and decodes it to UTF-8.
        This is needed for dispatching RPCs with ncclient.

        Returns:
            str: The string representation of the filter_xml attribute.
        """

        return(ET.tostring(self.filter_xml).decode('utf-8'))
    
class DispatchFilter:
    def __init__(self):
        # Implemented in child classes
        pass

    def __str__(self):
        """
        This method converts the filter_xml attribute to a string using the
        ElementTree tostring method and decodes it to UTF-8.
        This is needed for dispatching RPCs with ncclient.

        Returns:
            str: The string representation of the filter_xml attribute.
        """

        return(ET.tostring(self.filter_xml).decode('utf-8'))
    
    def __ele__(self):
        """
        This method converts the filter_xml attribute to an Element object.
        This is needed for dispatching RPCs with ncclient.

        Returns:
            xml.etree.ElementTree.Element: The Element object of the filter_xml attribute.

        Resources:
            https://github.com/ncclient/ncclient/issues/182
        """

        return(to_ele(str(self)))