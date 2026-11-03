{# Use the layer name as the schema (bronze/silver/gold/ref) instead of dbt's default prefixing. #}
{% macro generate_schema_name(custom_schema_name, node) -%}
  {{ custom_schema_name if custom_schema_name else target.schema }}
{%- endmacro %}
