.headers on

select first_name, last_name, nick, email, exit_date from member
where exit_date is null and (email is null or email == '');
