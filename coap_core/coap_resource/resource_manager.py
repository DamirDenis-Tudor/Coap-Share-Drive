from coap_core.coap_resource.resource import Resource
from coap_core.coap_utilities.coap_singleton import CoapSingletonBase


class ResourceManager(CoapSingletonBase):
    """
    The `ResourceManager` class manages CoAP resources within a CoAP core component.
    Usage:
    - Example usage might involve creating a single instance of the ResourceManager and adding resources to it.

    Notes:
    - Ensure proper initialization and handling of ResourceManager attributes before use.
    - Inherits from `CoapSingletonBase` to enforce a singleton pattern,
      allowing only one instance of ResourceManager.
    - The `discover_resources` method is currently a placeholder and needs
      to be implemented for actual resource discovery logic.

    """
    def __init__(self):
        # List to store CoAP resources
        self.__resources: list = []
        # Default CoAP resource
        self.__default_resource = None

    def add_resource(self, resource: Resource):
        """Adds a CoAP resource to the ResourceManager."""
        self.__resources.append(resource)

    def add_default_resource(self, resource: Resource):
        """Sets the default CoAP resource for the ResourceManager."""
        self.__default_resource = resource

    def get_resource(self, name: str) -> Resource | None:
        """
        Retrieves a CoAP resource by name.

        Returns:
        - `Resource`: The CoAP resource with the specified name.
        - `None`: If no resource is found with the given name.
        """
        for resource in self.__resources:
            if resource.get_name() == name:
                return resource
        return None

    def get_default_resource(self):
        """Retrieves the default CoAP resource."""
        return self.__default_resource

    def discover_resources(self):
        """Placeholder method for discovering CoAP resources; currently empty."""
        pass