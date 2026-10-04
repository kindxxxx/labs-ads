-- PAWS: Telegram lab order service schema

create table if not exists public.users (
  id bigserial primary key,
  telegram_id bigint not null unique,
  username varchar(64),
  first_name varchar(128),
  last_name varchar(128),
  photo_url varchar(512),
  language_code varchar(8),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists ix_users_telegram_id on public.users (telegram_id);

create table if not exists public.subject_credentials (
  id bigserial primary key,
  user_id bigint not null references public.users (id) on delete cascade,
  subject varchar(8) not null,
  login varchar(128) not null,
  password_encrypted text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, subject)
);

create index if not exists ix_subject_credentials_user_id on public.subject_credentials (user_id);

create table if not exists public.languages (
  id serial primary key,
  name varchar(32) not null unique
);

create table if not exists public.labs (
  id serial primary key,
  subject varchar(8) not null,
  lab_number integer not null,
  price integer not null,
  description text not null default '',
  requirements text not null default '',
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  unique (subject, lab_number)
);

create index if not exists ix_labs_subject on public.labs (subject);

create table if not exists public.lab_languages (
  lab_id integer not null references public.labs (id) on delete cascade,
  language_id integer not null references public.languages (id) on delete cascade,
  primary key (lab_id, language_id)
);

create table if not exists public.orders (
  id bigserial primary key,
  user_id bigint not null references public.users (id) on delete cascade,
  status varchar(32) not null default 'awaiting_payment',
  total_price integer not null,
  admin_comment text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists ix_orders_user_id on public.orders (user_id);
create index if not exists ix_orders_status on public.orders (status);

create table if not exists public.order_items (
  id bigserial primary key,
  order_id bigint not null references public.orders (id) on delete cascade,
  lab_id integer not null references public.labs (id),
  language_id integer references public.languages (id),
  price integer not null,
  unique (order_id, lab_id)
);

create index if not exists ix_order_items_order_id on public.order_items (order_id);

create table if not exists public.attachments (
  id bigserial primary key,
  order_id bigint not null references public.orders (id) on delete cascade,
  kind varchar(32) not null,
  storage_path varchar(512),
  original_name varchar(256) not null,
  mime_type varchar(128) not null,
  size_bytes bigint not null,
  telegram_file_id varchar(256),
  created_at timestamptz not null default now()
);

create index if not exists ix_attachments_order_id on public.attachments (order_id);

create table if not exists public.github_links (
  id bigserial primary key,
  order_id bigint not null references public.orders (id) on delete cascade,
  url varchar(2048) not null,
  link_type varchar(16) not null,
  created_at timestamptz not null default now()
);

create index if not exists ix_github_links_order_id on public.github_links (order_id);

create table if not exists public.payments (
  id bigserial primary key,
  order_id bigint not null unique references public.orders (id) on delete cascade,
  amount integer not null,
  status varchar(16) not null default 'pending',
  receipt_attachment_id bigint references public.attachments (id),
  user_chat_id bigint,
  user_message_id bigint,
  admin_chat_id bigint,
  admin_message_id bigint,
  confirmed_by bigint,
  confirmed_at timestamptz,
  rejection_reason text,
  created_at timestamptz not null default now()
);

create table if not exists public.order_status_history (
  id bigserial primary key,
  order_id bigint not null references public.orders (id) on delete cascade,
  old_status varchar(32),
  new_status varchar(32) not null,
  changed_by bigint not null default 0,
  comment text,
  created_at timestamptz not null default now()
);

create index if not exists ix_order_status_history_order_id on public.order_status_history (order_id);

-- RLS: backend uses postgres/service connection; block public API access by default.
alter table public.users enable row level security;
alter table public.subject_credentials enable row level security;
alter table public.languages enable row level security;
alter table public.labs enable row level security;
alter table public.lab_languages enable row level security;
alter table public.orders enable row level security;
alter table public.order_items enable row level security;
alter table public.attachments enable row level security;
alter table public.github_links enable row level security;
alter table public.payments enable row level security;
alter table public.order_status_history enable row level security;
