#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "OrchardScene.generated.h"

// Centimetres in UE; synthetic terrain, not a surveyed orchard.
UCLASS()
class BLOCKS_API AOrchardScene : public AActor
{
    GENERATED_BODY()
public:
    AOrchardScene();
    virtual void OnConstruction(const FTransform& Transform) override;
    static float GroundHeight(float X, float Y);
private:
    UPROPERTY() class UProceduralMeshComponent* Terrain;
    UPROPERTY() class UInstancedStaticMeshComponent* Trunks;
    UPROPERTY() class UInstancedStaticMeshComponent* Leaves;
    UPROPERTY() class UInstancedStaticMeshComponent* Fruit;
    UPROPERTY() class UInstancedStaticMeshComponent* Shrubs;
    UPROPERTY() class UInstancedStaticMeshComponent* Road;
    UPROPERTY() class UInstancedStaticMeshComponent* Pad;
};

UCLASS()
class BLOCKS_API AOrchardMacaque : public AActor
{
    GENERATED_BODY()
public:
    AOrchardMacaque();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    UPROPERTY(EditAnywhere, Category="Orchard") int32 Individual = 0;
private:
    UPROPERTY() TArray<class UStaticMeshComponent*> Limbs;
    UPROPERTY() class UStaticMeshComponent* Head;
    FVector Centre;
    float Elapsed = 0;
};
