-- 'o2net.group_vendor'
update o2net_quotation 
set "group" = 'o2net.group_vendor'
from  o2net_quotation_assigned_rel a 
where
o2net_quotation.id = a.o2net_quotation_id
and o2net_quotation.vendor_id in ( a.res_partner_id );

-- 'o2net.group_pm'
update o2net_quotation 
set "group" = 'o2net.group_pm'
from  o2net_quotation_assigned_rel a 
where
o2net_quotation.id = a.o2net_quotation_id
and o2net_quotation.pm_id in ( a.res_partner_id );

-- 'o2net.group_pc'
update o2net_quotation 
set "group" = 'o2net.group_pc'
from  o2net_quotation_assigned_rel a 
where
o2net_quotation.id = a.o2net_quotation_id
and o2net_quotation.pc_id in ( a.res_partner_id );

-- 'o2net.group_manager'
update o2net_quotation
set "group" = 'o2net.group_manager'
from o2net_quotation_assigned_rel a 
where
o2net_quotation.id = a.o2net_quotation_id
and exists ( select 1 from o2net_quotation_manager_rel aa where aa.o2net_quotation_id = o2net_quotation.id and a.res_partner_id = aa.res_partner_id );

