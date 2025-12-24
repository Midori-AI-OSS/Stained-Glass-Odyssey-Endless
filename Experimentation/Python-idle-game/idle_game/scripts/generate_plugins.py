"""Generate idle game character plugins from backend plugins."""
import ast
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Optional

# Backend plugins directory
BACKEND_PLUGINS_DIR = Path(__file__).parent.parent.parent.parent.parent / "backend" / "plugins" / "characters"
# Idle game plugins directory
IDLE_PLUGINS_DIR = Path(__file__).parent.parent / "plugins" / "characters"


def get_value(node):
    """Extract value from AST node."""
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.List):
        return [get_value(el) for el in node.elts]
    elif isinstance(node, ast.Dict):
        return {get_value(k): get_value(v) for k, v in zip(node.keys, node.values)}
    elif isinstance(node, ast.Attribute):
        return node.attr
    elif isinstance(node, ast.Call):
        for kw in node.keywords:
            if kw.arg == "default_factory":
                if isinstance(kw.value, ast.Lambda):
                    return get_value(kw.value.body)
                elif isinstance(kw.value, ast.Name):
                    return kw.value.id
        for kw in node.keywords:
            if kw.arg == "default":
                return get_value(kw.value)
        if isinstance(node.func, ast.Name):
            return node.func.id
    return None


def parse_backend_character(file_path: Path) -> Optional[Dict[str, Any]]:
    """Parse backend character plugin file."""
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except SyntaxError:
        print(f"Error parsing {file_path}")
        return None

    char_class = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            char_class = node
            break

    if not char_class:
        return None

    data = {
        "id": "",
        "name": "",
        "short_lore": "",
        "full_lore": "",
        "char_type": "C",
        "gacha_rarity": 0,
        "damage_type": "Physical",
        "passives": [],
        "special_abilities": [],
        "ui": {},
        "base_stats": {
            "max_hp": 1000,
            "atk": 100,
            "defense": 50,
            "mitigation": 1.0,
            "base_aggro": 1.0,
            "crit_rate": 0.05,
            "crit_damage": 2.0,
            "effect_hit_rate": 1.0,
            "regain": 0,
            "dodge_odds": 0.0,
            "effect_resistance": 0.0,
            "vitality": 1.0,
        },
        "growth": {},
        "metadata": {},
    }

    # Parse class attributes
    for node in char_class.body:
        if isinstance(node, ast.Assign) or isinstance(node, ast.AnnAssign):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            target_name = targets[0].id if isinstance(targets[0], ast.Name) else None

            if not target_name:
                continue

            value = node.value if isinstance(node, ast.Assign) else node.value
            if not value:
                continue

            val = get_value(value)

            if target_name == "id":
                data["id"] = val
            elif target_name == "name":
                data["name"] = val
            elif target_name == "summarized_about":
                data["short_lore"] = val
            elif target_name == "full_about":
                data["full_lore"] = val
            elif target_name == "char_type":
                data["char_type"] = val
            elif target_name == "gacha_rarity":
                data["gacha_rarity"] = val
            elif target_name == "damage_type":
                data["damage_type"] = str(val)
            elif target_name == "passives":
                data["passives"] = val if isinstance(val, list) else []
            elif target_name == "special_abilities":
                data["special_abilities"] = val if isinstance(val, list) else []
            elif target_name == "stat_gain_map":
                data["growth"]["stat_gain_map"] = val
            elif target_name == "ui_portrait_pool":
                data["ui"]["portrait_pool"] = val
            elif target_name == "ui_non_selectable":
                data["ui"]["non_selectable"] = val

    # Parse __post_init__ for base_stat overrides
    for node in char_class.body:
        if isinstance(node, ast.FunctionDef) and node.name == "__post_init__":
            for stmt in node.body:
                if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                    func = stmt.value.func
                    if isinstance(func, ast.Attribute) and func.attr == "set_base_stat":
                        args = stmt.value.args
                        if len(args) >= 2:
                            key = get_value(args[0])
                            val = get_value(args[1])
                            if key and val is not None:
                                data["base_stats"][key] = val

                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if (
                            isinstance(target, ast.Attribute)
                            and isinstance(target.value, ast.Name)
                            and target.value.id == "self"
                        ):
                            key = target.attr
                            val = get_value(stmt.value)

                            clean_key = key.replace("_base_", "")
                            if clean_key == "hp":
                                clean_key = "max_hp"

                            accepted_stats = [
                                "base_aggro",
                                "max_hp",
                                "atk",
                                "defense",
                                "mitigation",
                                "crit_rate",
                                "crit_damage",
                                "effect_hit_rate",
                                "regain",
                                "dodge_odds",
                                "effect_resistance",
                                "vitality",
                            ]

                            if clean_key in accepted_stats:
                                if isinstance(val, (int, float)):
                                    data["base_stats"][clean_key] = val

    if not data["id"]:
        return None

    # Set UI portrait path
    assets_dir = Path(__file__).parent.parent / "assets" / "characters"
    portrait_dir = assets_dir / data["id"]
    portrait_file = assets_dir / f"{data['id']}.png"

    if portrait_dir.exists() and portrait_dir.is_dir():
        data["ui"]["portrait"] = str(portrait_dir)
    elif portrait_file.exists():
        data["ui"]["portrait"] = str(portrait_file)

    return data


def generate_character_plugin(data: Dict[str, Any]) -> str:
    """Generate Python code for idle game character plugin."""
    # Format lists and dicts
    def format_list(lst):
        if not lst:
            return "[]"
        items = ", ".join(f'"{item}"' if isinstance(item, str) else str(item) for item in lst)
        return f"[{items}]"

    def format_dict(d):
        if not d:
            return "{}"
        items = []
        for k, v in d.items():
            if isinstance(v, str):
                items.append(f'"{k}": "{v}"')
            else:
                items.append(f'"{k}": {v}')
        return "{" + ", ".join(items) + "}"

    # Build the class
    code = f'''"""Character plugin: {data['name']}."""
from dataclasses import dataclass, field
from plugins.characters._base import IdleCharacter


@dataclass
class {data['name'].replace(" ", "")}(IdleCharacter):
    """Character: {data['name']}."""
    
    id: str = "{data['id']}"
    name: str = "{data['name']}"
    short_lore: str = """{data['short_lore']}"""
    full_lore: str = """{data['full_lore']}"""
    char_type: str = "{data['char_type']}"
    gacha_rarity: int = {data['gacha_rarity']}
    damage_type: str = "{data['damage_type']}"
    passives: list = field(default_factory=lambda: {format_list(data['passives'])})
    special_abilities: list = field(default_factory=lambda: {format_list(data['special_abilities'])})
'''

    # Add UI if present
    if data.get("ui"):
        code += f'    ui: dict = field(default_factory=lambda: {format_dict(data["ui"])})\n'

    # Add base stats
    code += '    base_stats: dict = field(default_factory=lambda: {\n'
    for key, val in data["base_stats"].items():
        code += f'        "{key}": {val},\n'
    code += '    })\n'

    return code


def main():
    """Generate all character plugins."""
    IDLE_PLUGINS_DIR.mkdir(parents=True, exist_ok=True)

    generated = 0
    for file_path in BACKEND_PLUGINS_DIR.glob("*.py"):
        if (
            file_path.name.startswith("_")
            or file_path.name == "slime.py"
            or file_path.name == "foe_base.py"
            or file_path.name == "player.py"
        ):
            continue

        print(f"Processing {file_path.name}...")
        data = parse_backend_character(file_path)
        if data:
            code = generate_character_plugin(data)
            output_file = IDLE_PLUGINS_DIR / file_path.name
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(code)
            print(f"  Generated {output_file.name}")
            generated += 1

    print(f"\nGenerated {generated} character plugins")


if __name__ == "__main__":
    main()
