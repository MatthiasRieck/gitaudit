"""Root GraphQL Class
"""

from pydantic import BaseModel, root_validator, Extra
from humps.camel import case


class GraphQlBase(BaseModel):
    """Root Graph QL Class"""
    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic Config for GraphQlBase"""
        alias_generator = case
        allow_population_by_field_name = True
        extra = Extra.forbid

    @root_validator(pre=True)
    def unwap_nodes(cls, data: dict):  # pylint: disable=no-self-argument
        """Unwraps <object>.nodes.<items> to <object>.<items>

        Args:
            data (dict): The to be validated input data

        Returns:
            dict: The valiated and transformed input data
        """
        for key, value in data.items():
            if isinstance(value, dict) and 'nodes' in value:
                data[key] = value['nodes']

        return data
