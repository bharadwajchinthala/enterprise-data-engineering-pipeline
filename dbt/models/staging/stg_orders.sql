select
    order_id,
    customer_id,
    product_id,
    order_date,
    quantity,
    unit_price,
    status,
    quantity * unit_price as gross_amount
from {{ source('retail_raw', 'raw_orders') }}
where quantity > 0
  and unit_price >= 0
  and status in ('completed', 'cancelled', 'returned')
qualify row_number() over (partition by order_id order by order_date desc) = 1
