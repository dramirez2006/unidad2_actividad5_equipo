-- Catálogo y matriz activa; comparar por códigos, no solo por cantidades.
SELECT id, code, is_active FROM roles ORDER BY code;
SELECT id, code, is_active FROM permissions ORDER BY code;
SELECT r.code AS rol, p.code AS permiso, rp.id AS relacion_id, rp.is_active AS relacion_activa,
       p.is_active AS permiso_activo
FROM role_permissions rp
JOIN roles r ON r.id = rp.role_id
JOIN permissions p ON p.id = rp.permission_id
ORDER BY r.code, p.code;

SELECT r.code AS rol, p.code AS permiso
FROM role_permissions rp
JOIN roles r ON r.id = rp.role_id
JOIN permissions p ON p.id = rp.permission_id
WHERE rp.is_active = 1 AND p.is_active = 1
ORDER BY r.code, p.code;

SELECT role_id, permission_id, COUNT(*) AS repeticiones
FROM role_permissions
GROUP BY role_id, permission_id
HAVING COUNT(*) > 1;

-- Identificar IDs reales antes de editar variables/*.json.
SELECT cu.id AS membresia_id, u.name, cu.company_id
FROM company_users cu JOIN users u ON u.id = cu.user_id
ORDER BY cu.id;

-- Preparación E06: ejecutar solo una variante y restaurarla inmediatamente.
-- Sustituir los IDs por los de la instalación local.
-- UPDATE roles SET is_active = 0 WHERE code = 'CONSULTA';
-- UPDATE roles SET is_active = 1 WHERE code = 'CONSULTA';
-- UPDATE permissions SET is_active = 0 WHERE code = 'concepts.write';
-- UPDATE permissions SET is_active = 1 WHERE code = 'concepts.write';

-- E08: la consulta debe dar cero, aunque sus filas sigan presentes inactivas.
SELECT COUNT(*) AS concesiones_capturista
FROM role_permissions rp JOIN roles r ON r.id = rp.role_id
WHERE r.code = 'CAPTURISTA' AND rp.is_active = 1;
