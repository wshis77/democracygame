/* find double voting rows */
SELECT bad_rows.* 
FROM votes as bad_rows
INNER JOIN(
SELECT  MIN(id) as min_id, votes.object_id, votes.user_id 
FROM votes where is_archived=FALSE and votes.direction < 20 and votes.content_type_id=11

GROUP BY votes.object_id, votes.user_id
having COUNT(votes.object_id) > 1
) as double_rows on double_rows.object_id = bad_rows.object_id and double_rows.user_id=bad_rows.user_id and bad_rows.is_archived=False
	and double_rows.min_id <> bad_rows.id
	 /*order by bad_rows.time_stamp DESC*/
