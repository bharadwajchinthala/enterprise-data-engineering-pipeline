-- Read validated Silver orders produced by PySpark, not the original raw CSV.
-- Preserve Spark's gross_amount rather than independently recalculating it.
select
    order_id,
    customer_id,
    product_id,
    order_date,
    quantity,
    unit_price,
    status,
    gross_amount
from {{ source('retail_silver', 'silver_orders') }}
where order_id is not null
  and order_date is not null
  and quantity > 0
  and unit_price >= 0
  and status in ('completed', 'cancelled', 'returned')
qualify row_number() over (partition by order_id order by order_date desc) = 1
