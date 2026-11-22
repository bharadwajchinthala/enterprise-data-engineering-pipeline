select
    order_date,
    count(*) as completed_order_count,
    sum(gross_amount) as gross_revenue
from {{ ref('stg_orders') }}
where status = 'completed'
group by order_date
