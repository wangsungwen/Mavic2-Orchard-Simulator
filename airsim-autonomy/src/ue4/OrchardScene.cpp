#include "OrchardScene.h"
#include "ProceduralMeshComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

namespace {
UStaticMesh* Shape(const TCHAR* Name) {
    return LoadObject<UStaticMesh>(nullptr, *FString::Printf(TEXT("/Engine/BasicShapes/%s.%s"), Name, Name));
}
UMaterialInterface* Mat(const TCHAR* Name) {
    return LoadObject<UMaterialInterface>(nullptr, *FString::Printf(TEXT("/Game/Orchard/Materials/M_%s.M_%s"), Name, Name));
}
void Instance(UInstancedStaticMeshComponent* C, FVector P, FVector S, FRotator R = FRotator::ZeroRotator) {
    C->AddInstance(FTransform(R, P, S));
}
}

float AOrchardScene::GroundHeight(float X, float Y) {
    const float Uphill = FMath::Max(0.f, X + 2500.f);
    const float Blend = FMath::Clamp(Uphill / 1500.f, 0.f, 1.f);
    return Uphill * 0.16f + Blend * (45.f * FMath::Sin(X / 1100.f) * FMath::Cos(Y / 1400.f));
}

AOrchardScene::AOrchardScene() {
    RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    Terrain = CreateDefaultSubobject<UProceduralMeshComponent>(TEXT("Hillside"));
    Terrain->SetupAttachment(RootComponent);
    Terrain->SetCollisionProfileName(TEXT("BlockAll"));
    Terrain->bUseComplexAsSimpleCollision = true;
    auto Make = [this](const TCHAR* Name, const TCHAR* Mesh, bool Collision) {
        auto* C = CreateDefaultSubobject<UInstancedStaticMeshComponent>(Name);
        C->SetupAttachment(RootComponent);
        C->SetStaticMesh(Shape(Mesh));
        C->SetCollisionProfileName(Collision ? TEXT("BlockAll") : TEXT("NoCollision"));
        return C;
    };
    Trunks = Make(TEXT("TreeTrunks"), TEXT("Cylinder"), true);
    Leaves = Make(TEXT("TreeCrowns"), TEXT("Sphere"), false);
    Fruit = Make(TEXT("CitrusFruit"), TEXT("Sphere"), false);
    Shrubs = Make(TEXT("Shrubs"), TEXT("Sphere"), false);
    Road = Make(TEXT("FarmTrack"), TEXT("Cube"), false);
    Pad = Make(TEXT("LandingPad"), TEXT("Cube"), true);
}

void AOrchardScene::OnConstruction(const FTransform& Transform) {
    Super::OnConstruction(Transform);
    Terrain->SetMaterial(0, Mat(TEXT("Ground")));
    Trunks->SetMaterial(0, Mat(TEXT("Bark")));
    Leaves->SetMaterial(0, Mat(TEXT("Leaves")));
    Fruit->SetMaterial(0, Mat(TEXT("Orange")));
    Shrubs->SetMaterial(0, Mat(TEXT("Shrub")));
    Road->SetMaterial(0, Mat(TEXT("Track")));
    Pad->SetMaterial(0, Mat(TEXT("Pad")));
    for (auto* C : {Trunks, Leaves, Fruit, Shrubs, Road, Pad}) C->ClearInstances();
    TArray<FVector> V, N;
    TArray<int32> T;
    TArray<FVector2D> UV;
    TArray<FLinearColor> Colors;
    TArray<FProcMeshTangent> Tangents;
    constexpr int32 Size = 101;
    for (int32 Y=0; Y<Size; ++Y) for (int32 X=0; X<Size; ++X) {
        float PX = -5000.f + X * 100.f, PY = -5000.f + Y * 100.f;
        V.Add(FVector(PX, PY, GroundHeight(PX,PY)));
        float DX = (GroundHeight(PX+1,PY)-GroundHeight(PX-1,PY))/2.f;
        float DY = (GroundHeight(PX,PY+1)-GroundHeight(PX,PY-1))/2.f;
        N.Add(FVector(-DX,-DY,1).GetSafeNormal()); UV.Add(FVector2D(X/10.f,Y/10.f));
        if (X<Size-1 && Y<Size-1) {
            int32 A=Y*Size+X;
            T.Append({A,A+Size,A+1,A+1,A+Size,A+Size+1});
        }
    }
    Terrain->CreateMeshSection_LinearColor(0,V,T,N,UV,Colors,Tangents,true);
    FRandomStream Random(20261018);
    for (int32 Row=0; Row<8; ++Row) for (int32 Col=-4; Col<=4; ++Col) {
        if (Col==0) continue; // central farm track
        float X=-1800.f+Row*800.f+Random.FRandRange(-60,60);
        float Y=Col*900.f+Random.FRandRange(-60,60);
        float Z=GroundHeight(X,Y), H=Random.FRandRange(270,350);
        Instance(Trunks,FVector(X,Y,Z+H*.35f),FVector(.22f,.22f,H*.007f));
        for (int32 L=0; L<7; ++L) {
            float A=L*2.f*PI/6.f;
            FVector P(X+FMath::Cos(A)*75,Y+FMath::Sin(A)*75,Z+H-50+(L==6?65:0));
            Instance(Leaves,P,FVector(1.85f,1.7f,1.65f));
        }
        for (int32 F=0; F<24; ++F) {
            float A=Random.RandRange(0,5)*2.f*PI/6.f, E=Random.FRandRange(-1.15f,1.15f);
            // Place fruit on the crown lobes rather than in a bounding box,
            // which would leave some oranges floating above the foliage.
            Instance(Fruit,FVector(X+FMath::Cos(A)*(75+92.5f*FMath::Cos(E)),
                Y+FMath::Sin(A)*(75+85.f*FMath::Cos(E)),Z+H-50+82.5f*FMath::Sin(E)),FVector(.095f));
        }
    }
    for (int32 I=0; I<180; ++I) {
        float X=Random.FRandRange(-2100,4700),Y=Random.FRandRange(-4600,4600);
        if (FMath::Abs(Y)<400) continue;
        Instance(Shrubs,FVector(X,Y,GroundHeight(X,Y)+25),FVector(Random.FRandRange(.6f,1.4f),.8f,.65f));
    }
    for (int32 I=0; I<90; ++I) {
        float X=-4500+I*100.f;
        float Pitch=FMath::RadiansToDegrees(FMath::Atan2(GroundHeight(X+50,0)-GroundHeight(X-50,0),100.f));
        Instance(Road,FVector(X,0,GroundHeight(X,0)+2),FVector(1.04f,5.f,.04f),FRotator(Pitch,0,0));
    }
    Instance(Pad,FVector(-3600,0,5),FVector(10,10,.1f));
}

AOrchardMacaque::AOrchardMacaque() {
    PrimaryActorTick.bCanEverTick = true;
    RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    auto Part = [this](const TCHAR* Name,FVector P,FVector Scale,const TCHAR* Material) {
        auto* C=CreateDefaultSubobject<UStaticMeshComponent>(Name);
        C->SetupAttachment(RootComponent); C->SetStaticMesh(Shape(TEXT("Sphere")));
        C->SetRelativeLocation(P); C->SetRelativeScale3D(Scale);
        C->SetMaterial(0,Mat(Material)); C->SetCollisionProfileName(TEXT("NoCollision"));
        C->SetMobility(EComponentMobility::Movable);
        return C;
    };
    Part(TEXT("Torso"),FVector(0,0,40),FVector(.62f,.32f,.35f),TEXT("Fur"));
    Head=Part(TEXT("Head"),FVector(30,0,58),FVector(.26f,.25f,.28f),TEXT("Fur"));
    Part(TEXT("Face"),FVector(41,0,56),FVector(.12f,.19f,.18f),TEXT("Face"));
    Part(TEXT("EarL"),FVector(29,-13,60),FVector(.1f,.055f,.12f),TEXT("Face"));
    Part(TEXT("EarR"),FVector(29,13,60),FVector(.1f,.055f,.12f),TEXT("Face"));
    Part(TEXT("EyeL"),FVector(46,-5,60),FVector(.025f),TEXT("Bark"));
    Part(TEXT("EyeR"),FVector(46,5,60),FVector(.025f),TEXT("Bark"));
    auto* Tail=Part(TEXT("Tail"),FVector(-45,0,38),FVector(.55f,.055f,.055f),TEXT("Fur"));
    Tail->SetRelativeRotation(FRotator(-18,0,0));
    for (int I=0; I<4; ++I) {
        auto* Limb=Part(*FString::Printf(TEXT("Limb%d"),I),FVector(I<2?22:-21,I%2?12:-12,21),FVector(.095f,.095f,.4f),TEXT("Fur"));
        Limbs.Add(Limb);
    }
}
void AOrchardMacaque::BeginPlay() {
    Super::BeginPlay();
    // AirSim rebases the world around PlayerStart during startup. Keep paths
    // in map coordinates so subsequent rebasing does not displace animals.
    Centre=GetActorLocation()+FVector(GetWorld()->OriginLocation);
}
void AOrchardMacaque::Tick(float Dt) {
    Super::Tick(Dt); Elapsed+=Dt;
    // Four seconds of pause/foraging after every twelve seconds of travel.
    const float Time=Elapsed+Individual*3.f;
    const float Cycle=FMath::Fmod(Time,16.f);
    const bool Moving=Cycle<12.f;
    const float Travel=FMath::FloorToFloat(Time/16.f)*12.f+FMath::Min(Cycle,12.f);
    const float Angle=Travel*.18f+Individual;
    const float X=Centre.X+260*FMath::Cos(Angle),Y=Centre.Y+180*FMath::Sin(Angle);
    SetActorLocation(FVector(X,Y,AOrchardScene::GroundHeight(X,Y)+3)-FVector(GetWorld()->OriginLocation));
    SetActorRotation(FRotator(0,FMath::RadiansToDegrees(FMath::Atan2(180*FMath::Cos(Angle),-260*FMath::Sin(Angle))),0));
    for (int I=0; I<Limbs.Num(); ++I) Limbs[I]->SetRelativeRotation(FRotator(Moving?28*FMath::Sin(Time*8+(I==0||I==3?0:PI)):0,0,0));
    Head->SetRelativeLocation(FVector(30,0,Moving?58:51+3*FMath::Sin(Time*3)));
}
