"""Philippine locations for the location dropdown."""

CITIES = [
    "Manila", "Quezon City", "Makati", "Taguig", "Pasig", "Mandaluyong", "San Juan",
    "Pasay", "Parañaque", "Las Piñas", "Muntinlupa", "Caloocan", "Malabon",
    "Navotas", "Valenzuela", "Marikina", "Pateros",
    "Baguio City", "Angeles City", "Clark", "Olongapo City", "Subic", "Dagupan",
    "San Fernando (La Union)", "San Fernando (Pampanga)", "Laoag", "Vigan",
    "Tuguegarao", "Santiago City", "Cabanatuan", "Tarlac City", "Malolos",
    "Batangas City", "Lipa", "Calamba", "Santa Rosa", "Biñan", "San Pablo",
    "Antipolo", "Bacoor", "Dasmariñas", "Imus", "Lucena", "Naga City",
    "Legazpi City", "Puerto Princesa",
    "Cebu City", "Mandaue", "Lapu-Lapu", "Iloilo City", "Bacolod", "Tacloban",
    "Dumaguete", "Tagbilaran", "Roxas City", "Kalibo",
    "Davao City", "Cagayan de Oro", "General Santos", "Zamboanga City", "Butuan",
    "Cotabato City", "Iligan", "Koronadal",
]

PROVINCES = (
    "Abra, Agusan del Norte, Agusan del Sur, Aklan, Albay, Antique, Apayao, Aurora, "
    "Basilan, Bataan, Batanes, Batangas, Benguet, Biliran, Bohol, Bukidnon, Bulacan, "
    "Cagayan, Camarines Norte, Camarines Sur, Camiguin, Capiz, Catanduanes, Cavite, "
    "Cebu, Cotabato, Davao de Oro, Davao del Norte, Davao del Sur, Davao Occidental, "
    "Davao Oriental, Dinagat Islands, Eastern Samar, Guimaras, Ifugao, Ilocos Norte, "
    "Ilocos Sur, Iloilo, Isabela, Kalinga, La Union, Laguna, Lanao del Norte, "
    "Lanao del Sur, Leyte, Maguindanao del Norte, Maguindanao del Sur, Marinduque, "
    "Masbate, Misamis Occidental, Misamis Oriental, Mountain Province, "
    "Negros Occidental, Negros Oriental, Northern Samar, Nueva Ecija, Nueva Vizcaya, "
    "Occidental Mindoro, Oriental Mindoro, Palawan, Pampanga, Pangasinan, Quezon, "
    "Quirino, Rizal, Romblon, Samar, Sarangani, Siquijor, Sorsogon, South Cotabato, "
    "Southern Leyte, Sultan Kudarat, Sulu, Surigao del Norte, Surigao del Sur, "
    "Tarlac, Tawi-Tawi, Zambales, Zamboanga del Norte, Zamboanga del Sur, "
    "Zamboanga Sibugay"
).split(", ")

LOCATIONS = ["Remote", "Abroad"] + CITIES + PROVINCES