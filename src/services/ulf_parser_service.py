import frontmatter
import yaml
from typing import Dict, List, Any

from src.core.errors import ParsingError


class ULFParserService:
    @staticmethod
    def parse(text_content: str) -> Dict[str, Any]:
        try:
            # Parse frontmatter using python-frontmatter
            post = frontmatter.loads(text_content)
            frontmatter_data = post.metadata
            body = post.content

            # Split body into cells by '---'
            cell_parts = body.split('---')
            cells = []

            # Each cell should have config and content, so even number of parts
            if len(cell_parts) % 2 != 0:
                raise ParsingError("Invalid structure: cells must have config and content separated by '---'")

            for i in range(0, len(cell_parts), 2):
                config_yaml = cell_parts[i].strip()
                content = cell_parts[i + 1].strip()

                # Parse YAML config
                try:
                    config = yaml.safe_load(config_yaml) or {}
                except yaml.YAMLError as e:
                    raise ParsingError(f"Invalid YAML in cell config: {e}")

                if not isinstance(config, dict):
                    raise ParsingError("Cell config must be a dictionary")

                cells.append({
                    'config': config,
                    'content': content
                })

            return {
                'frontmatter': frontmatter_data,
                'cells': cells
            }

        except (ValueError, yaml.YAMLError) as e:
            raise ParsingError(f"Invalid frontmatter: {e}")
        except Exception as e:
            raise ParsingError(f"Parsing error: {e}")

    @staticmethod
    def stringify(lesson_model: Dict[str, Any]) -> str:
        try:
            frontmatter_data = lesson_model.get('frontmatter', {})
            cells = lesson_model.get('cells', [])

            # Build frontmatter YAML
            frontmatter_yaml = yaml.dump(frontmatter_data, default_flow_style=False).strip()

            # Build body
            body_parts = []
            for cell in cells:
                config = cell.get('config', {})
                content = cell.get('content', '')

                # YAML for config
                config_yaml = yaml.dump(config, default_flow_style=False).strip()
                body_parts.append(config_yaml)
                body_parts.append(content)

            body = '\n---\n'.join(body_parts)

            # Combine
            result = f"---\n{frontmatter_yaml}\n---\n{body}"
            return result

        except Exception as e:
            raise ParsingError(f"Stringify error: {e}")
