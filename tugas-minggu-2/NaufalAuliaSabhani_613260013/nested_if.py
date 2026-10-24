nilai = 85
sikap = "baik"

if nilai >= 80:
    if sikap == "baik":
        print("Lulus dengan predikat sangat baik")
    else:
        print("Lulus dengan predikat baik")

if nilai >= 70:
    if sikap == "baik":
        print("Lulus dengan predikat baik")
    else:
        print("Lulus dengan predikat cukup")

else:
    print(" Maaf anda Tidak lulus")