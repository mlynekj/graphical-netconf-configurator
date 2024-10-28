def removeXmlns(element):
    """ Removes all namespace declarations from xml """
    element.tag = element.tag.split('}', 1)[-1]  # Remove namespace from the tag
    # Recursively apply to child elements
    for child in element:
        removeXmlns(child)