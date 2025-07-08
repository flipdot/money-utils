.headers on

select first_name, last_name, nick, email from member
where exit_date is null and email != '';
