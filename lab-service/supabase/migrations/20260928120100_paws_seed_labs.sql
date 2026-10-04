-- PAWS catalog seed (from config/labs.py)

insert into public.languages (name) values ('Python'), ('C++')
on conflict (name) do nothing;

-- PP1
insert into public.labs (subject, lab_number, price, description, requirements, is_active)
values
  ('PP1', 1, 1500, 'Лабораторная 1', '', true),
  ('PP1', 2, 1500, 'Лабораторная 2', '', true),
  ('PP1', 3, 1500, 'Лабораторная 3', '', true)
on conflict (subject, lab_number) do update set
  price = excluded.price,
  description = excluded.description,
  is_active = true;

-- PP2
insert into public.labs (subject, lab_number, price, description, requirements, is_active)
values
  ('PP2', 1, 1500, 'Лабораторная 1', '', true),
  ('PP2', 2, 1500, 'Лабораторная 2', '', true)
on conflict (subject, lab_number) do update set
  price = excluded.price,
  description = excluded.description,
  is_active = true;

-- ADS
insert into public.labs (subject, lab_number, price, description, requirements, is_active)
values
  ('ADS', 1, 2000, 'Лабораторная 1', '', true),
  ('ADS', 2, 2000, 'Лабораторная 2', '', true)
on conflict (subject, lab_number) do update set
  price = excluded.price,
  description = excluded.description,
  is_active = true;

-- lab_languages
insert into public.lab_languages (lab_id, language_id)
select l.id, lang.id
from public.labs l
cross join public.languages lang
where (l.subject, l.lab_number, lang.name) in (
  ('PP1', 1, 'Python'), ('PP1', 1, 'C++'),
  ('PP1', 2, 'Python'), ('PP1', 2, 'C++'),
  ('PP1', 3, 'Python'),
  ('PP2', 1, 'C++'), ('PP2', 2, 'C++'),
  ('ADS', 1, 'C++'), ('ADS', 2, 'C++')
)
on conflict do nothing;
