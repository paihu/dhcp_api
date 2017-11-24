drop table if exists dhcp;
create table dhcp (
   host text primary key,
   typeid integer not null ,
   mac  text not null unique,
   ip   text not null unique
);

drop table if exists asset;
create table asset (
   host text primary key,
   lan  text not null unique,
   wlan text not null unique
);

drop table if exists range;
create table range (
   typeid  integer primary key,
   start text not null unique,
   end   text not null unique,
   name  text not null unique
);

